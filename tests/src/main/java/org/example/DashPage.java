package org.example;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;

public class DashPage {
    private WebDriver driver;
    private WebDriverWait wait;

    // Локаторы
    private By generateBtn = By.id("generate-series-btn");
    private By seriesInfo = By.id("generated-series-info");
    private By logBox = By.id("log-container");
    private By historyTable = By.id("table-container");
    private By plotsBox = By.id("plots-container");
    private By add2dGraphBtn = By.id("add-plot-2d");
    private By startCalcBtn = By.xpath("//button[contains(text(),'Запустить расчеты')]");
    private By addRowBtn = By.xpath("//button[contains(text(),'Добавить строку')]");
    // Локатор для самого поля загрузки
    private By fileInput = By.cssSelector("#upload-parameters input[type='file']");
    // Локатор для текста, который сообщает о загрузке (зеленый текст на скрине)
    private By uploadStatus = By.id("uploaded-parameters-info");

    public DashPage(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    // --- МЕТОДЫ ДЛЯ ЗАДАНИЯ 2 ---

    public void clickGenerate() {
        driver.findElement(generateBtn).click();
    }

    public String getSeriesStatusText() {
        return driver.findElement(seriesInfo).getText();
    }

    public String getLogContent() {
        return driver.findElement(logBox).getText();
    }

    public boolean isHistoryVisible() {
        return driver.findElement(historyTable).isDisplayed();
    }

    public void clickAdd2DGraph() {
        driver.findElement(add2dGraphBtn).click();
    }

    public boolean arePlotsDisplayed() {
        return driver.findElement(plotsBox).isDisplayed();
    }

    public boolean isAddRowButtonEnabled() {
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(5));
        // Ждем, пока кнопка появится в DOM-дереве
        return wait.until(ExpectedConditions.presenceOfElementLocated(addRowBtn)).isEnabled();
    }

    public void clickStart() {
        driver.findElement(startCalcBtn).click();
    }

    public String getHistoryTableText() {
        return driver.findElement(historyTable).getText();
    }

    public void uploadFile(String absolutePath) {
        driver.findElement(fileInput).sendKeys(absolutePath);
    }

    public String getUploadStatusText() {
        try {
            // подождем 3 секунды, пока Dash обновит UI
            Thread.sleep(3000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        return driver.findElement(uploadStatus).getText();
    }
}