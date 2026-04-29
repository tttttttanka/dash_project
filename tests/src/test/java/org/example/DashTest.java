package org.example;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.testng.Assert;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.By;
import java.time.Duration;

public class DashTest {
    private WebDriver driver;
    private DashPage dashPage;

    @BeforeMethod
    public void setUp() {
        // 1. Укажи путь к yandexdriver.exe
        System.setProperty("webdriver.chrome.driver", "C:\\Users\\Дмитрий\\IdeaProjects\\OKIS_lab_5\\drivers\\chromedriver.exe");

        ChromeOptions options = new ChromeOptions();
        // 2. Укажи путь к самому Яндекс.Браузеру
        options.setBinary("C:\\Program Files\\Yandex\\YandexBrowser\\Application\\browser.exe");

        driver = new ChromeDriver(options);
        driver.manage().window().maximize();
        // URL твоего запущенного Dash-приложения
        driver.get("http://127.0.0.1:8050/");

        dashPage = new DashPage(driver);
    }

    // --- ПОЗИТИВНЫЕ ТЕСТЫ ---

    @Test(priority = 1)
    public void testPageTitle() {
        // Проверяем, что заголовок страницы верный
        Assert.assertTrue(driver.getPageSource().contains("Расчёт параметров"));
    }

    @Test(priority = 2)
    public void testGenerateSeries() throws InterruptedException {
        dashPage.clickGenerate();

        // Принудительная пауза на 2 секунды
        Thread.sleep(2000);

        String status = dashPage.getSeriesStatusText();
        // Проверяем наличие текста в принципе
        Assert.assertTrue(status.contains("Сгенерировано"));
    }

    @Test(priority = 3)
    public void testLogInitialText() {
        String logText = dashPage.getLogContent();
        Assert.assertEquals(logText, "Лог появится здесь после запуска");
    }

    @Test(priority = 4)
    public void testHistoryIsPresent() {
        Assert.assertTrue(dashPage.isHistoryVisible(), "Блок истории должен быть виден");
    }

    // --- НЕГАТИВНЫЕ ТЕСТЫ ---

    @Test(priority = 5)
    public void testCalcWithoutData() {
        // Нажимаем старт без загрузки файла и генерации
        dashPage.clickStart();
        // Проверяем, что лог остался прежним (расчет не пошел)
        Assert.assertEquals(dashPage.getLogContent(), "Лог появится здесь после запуска");
    }

    @Test(priority = 6)
    public void test2DGraphWithoutData() {
        dashPage.clickAdd2DGraph();
        // Проверяем, что блок графиков все еще пустой или не выдал ошибку
        Assert.assertTrue(dashPage.arePlotsDisplayed());
    }

    @Test(priority = 7)
    public void testAddRowButton() {
        // Теперь обращаемся через dashPage
        Assert.assertTrue(dashPage.isAddRowButtonEnabled(), "Кнопка 'Добавить строку' должна быть активна");
    }

    @Test(priority = 8)
    public void testEmptyHistoryOnStart() {
        // Получаем текст через метод DashPage
        String historyText = dashPage.getHistoryTableText();
        Assert.assertTrue(historyText.contains("Нет данных"), "В истории должно быть написано 'Нет данных'");
    }



    @AfterMethod
    public void tearDown() {
        if (driver != null) {
            driver.quit();
        }
    }
}